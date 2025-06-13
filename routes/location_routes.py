from flask import Blueprint, request, jsonify
from psycopg2.extras import RealDictCursor
from models.db import get_connection
from flasgger import swag_from
import psycopg2
import requests
import os
from dotenv import load_dotenv

location_bp = Blueprint('location', __name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY")

def reverse_geocode_locationiq(lat, lon):
    try:
        url = f"https://us1.locationiq.com/v1/reverse.php?key={LOCATIONIQ_API_KEY}&lat={lat}&lon={lon}&format=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        print(data)
        
        # Ambil nama kota dan alamat lengkap
        city = data.get("address", {}).get("city") or data.get("address", {}).get("town") or data.get("address", {}).get("village") or "Unknown"
        display_name = data.get("display_name", "Alamat tidak ditemukan")

        print(f"City: {city}, Display Name: {display_name}")
        
        return city, display_name
    except requests.RequestException as e:
        raise Exception(f"Gagal mengambil alamat dari LocationIQ: {e}")

@location_bp.route("/api/location", methods=["POST"])
@swag_from('docs/location/create_location.yml')
def create_location():
    """
    Endpoint untuk membuat lokasi baru berdasarkan koordinat.
    Nama dan alamat detail diambil otomatis dari LocationIQ.
    """
    try:
        data = request.json
        print(data)
        
        if not data:
            return jsonify({"error": "Data tidak boleh kosong"}), 400
            
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        
        if not all([latitude, longitude]):
            return jsonify({"error": "Field wajib: latitude, longitude"}), 400
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            return jsonify({"error": "Latitude dan longitude harus berupa angka"}), 400
        
        if not (-90 <= latitude <= 90):
            return jsonify({"error": "Latitude harus antara -90 sampai 90"}), 400
        if not (-180 <= longitude <= 180):
            return jsonify({"error": "Longitude harus antara -180 sampai 180"}), 400
        
        # Ambil kota dan alamat dari LocationIQ
        try:
            city_name, detail_address = reverse_geocode_locationiq(latitude, longitude)
        except Exception as e:
            print(f"Error fetching location data: {e}")
            return jsonify({"error": str(e)}), 500
        
        # Simpan ke database
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO locations (name, latitude, longitude, detail_address) 
                    VALUES (%s, %s, %s, %s) 
                    RETURNING id, name, latitude, longitude, detail_address
                """, (city_name, latitude, longitude, detail_address))
                
                new_location = cur.fetchone()
                conn.commit()
        
        return jsonify({
            "message": "Lokasi berhasil disimpan",
            "data": {
                "id": new_location["id"],
                "name": new_location["name"],
                "latitude": float(new_location["latitude"]),
                "longitude": float(new_location["longitude"]),
                "detail_address": new_location["detail_address"],
                # "created_at": new_location["created_at"].isoformat()
            }
        }), 201
        
    except psycopg2.Error as e:
        print(f"Error: {e}")
        return jsonify({
            "error": "Database error",
            "details": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@location_bp.route("/api/locations", methods=["GET"])
@swag_from('docs/location/list_locations.yml')
def get_locations():
    """
    Endpoint untuk mendapatkan daftar semua lokasi
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, latitude, longitude, detail_address, created_at 
                    FROM locations 
                    ORDER BY created_at DESC
                """)
                
                locations = cur.fetchall()
        
        # Format response
        locations_data = []
        for location in locations:
            locations_data.append({
                "id": location["id"],
                "name": location["name"],
                "latitude": float(location["latitude"]),
                "longitude": float(location["longitude"]),
                "detail_address": location["detail_address"],
                "created_at": location["created_at"].isoformat()
            })
        
        return jsonify({
            "message": "Berhasil mengambil data lokasi",
            "data": locations_data,
            "total": len(locations_data)
        }), 200
        
    except psycopg2.Error as e:
        return jsonify({
            "error": "Database error",
            "details": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


@location_bp.route("/api/location/<int:location_id>", methods=["GET"])
@swag_from('docs/location/get_location.yml')
def get_location(location_id):
    """
    Endpoint untuk mendapatkan detail lokasi berdasarkan ID
    """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, latitude, longitude, detail_address
                    FROM locations 
                    WHERE id = %s
                """, (location_id,))
                
                location = cur.fetchone()
        
        if not location:
            return jsonify({
                "error": "Lokasi tidak ditemukan"
            }), 404
        
        return jsonify({
            "message": "Berhasil mengambil detail lokasi",
            "data": {
                "id": location["id"],
                "name": location["name"],
                "latitude": float(location["latitude"]),
                "longitude": float(location["longitude"]),
                "detail_address": location["detail_address"],
                # "created_at": location["created_at"].isoformat()
            }
        }), 200
        
    except psycopg2.Error as e:
        return jsonify({
            "error": "Database error",
            "details": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500
