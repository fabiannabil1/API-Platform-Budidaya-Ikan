CREATE TABLE "role_change_requests" (
  "id" SERIAL PRIMARY KEY,
  "user_id" INTEGER NOT NULL,
  "reason" TEXT NOT NULL,
  "status" VARCHAR(20) DEFAULT 'pending',
  "requested_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "processed_at" TIMESTAMP,
  "processed_by" INTEGER,
  "rejection_reason" TEXT,
  CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_processor FOREIGN KEY (processed_by) REFERENCES users(id),
  CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- Add index for faster queries
CREATE INDEX idx_role_change_status ON role_change_requests(status);
CREATE INDEX idx_role_change_user ON role_change_requests(user_id);
