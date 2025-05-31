CREATE TABLE "users" (
  "id" SERIAL PRIMARY KEY,
  "name" VARCHAR(100),
  "phone" VARCHAR(20) UNIQUE,
  "password" TEXT,
  "role" VARCHAR(10),
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "user_profiles" (
  "id" SERIAL PRIMARY KEY,
  "user_id" INTEGER UNIQUE,
  "address" TEXT,
  "profile_picture" TEXT,
  "bio" TEXT
);

CREATE TABLE "locations" (
  "id" SERIAL PRIMARY KEY,
  "name" VARCHAR(100),
  "latitude" DECIMAL(10,6),
  "longitude" DECIMAL(10,6)
);

CREATE TABLE "auctions" (
  "id" SERIAL PRIMARY KEY,
  "user_id" INTEGER,
  "title" VARCHAR(255),
  "description" TEXT,
  "starting_price" NUMERIC(12,2),
  "current_price" NUMERIC(12,2),
  "deadline" TIMESTAMP,
  "location_id" INTEGER,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "status" VARCHAR(20) DEFAULT 'open'
);

CREATE TABLE "bids" (
  "id" SERIAL PRIMARY KEY,
  "auction_id" INTEGER,
  "user_id" INTEGER,
  "bid_amount" NUMERIC(12,2),
  "bid_time" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "products" (
  "id" SERIAL PRIMARY KEY,
  "name" VARCHAR(255),
  "description" TEXT,
  "price" NUMERIC(12,2),
  "stock" INTEGER,
  "image_url" TEXT,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "updated_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "created_by" INTEGER
);

CREATE TABLE "articles" (
  "id" SERIAL PRIMARY KEY,
  "title" VARCHAR(255),
  "content" TEXT,
  "image_url" TEXT,
  "created_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "updated_at" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "author_id" INTEGER
);

CREATE TABLE "orders" (
  "id" SERIAL PRIMARY KEY,
  "user_id" INTEGER,
  "order_date" TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
  "total_amount" NUMERIC(12,2),
  "status" VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE "order_items" (
  "id" SERIAL PRIMARY KEY,
  "order_id" INTEGER,
  "product_id" INTEGER,
  "quantity" INTEGER,
  "price" NUMERIC(12,2)
);

COMMENT ON COLUMN "users"."role" IS 'mitra, biasa, admin';

COMMENT ON COLUMN "auctions"."status" IS 'open, closed, cancelled';

COMMENT ON COLUMN "orders"."status" IS 'pending, paid, shipped, cancelled';

ALTER TABLE "user_profiles" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "auctions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "auctions" ADD FOREIGN KEY ("location_id") REFERENCES "locations" ("id");

ALTER TABLE "bids" ADD FOREIGN KEY ("auction_id") REFERENCES "auctions" ("id");

ALTER TABLE "bids" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "products" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id");

ALTER TABLE "articles" ADD FOREIGN KEY ("author_id") REFERENCES "users" ("id");

ALTER TABLE "orders" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "order_items" ADD FOREIGN KEY ("order_id") REFERENCES "orders" ("id");

ALTER TABLE "order_items" ADD FOREIGN KEY ("product_id") REFERENCES "products" ("id");
