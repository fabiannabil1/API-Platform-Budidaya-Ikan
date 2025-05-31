from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))



class Config:
    JWT_SECRET_KEY = os.getenv("JWT_KEY")
    SWAGGER = {
        "openapi": "3.0.1",
        "info": {
            "title": "API Efishery",
            "version": "1.0.0",
            "description": "API Clone untuk Efishery",
        },
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Masukkan token JWT Anda. Contoh: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`"
                }
            }
        },
        "security": [
            {
                "BearerAuth": []
            }
        ]
    }
