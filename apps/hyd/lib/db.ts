import { Pool } from "pg";

export const db = new Pool({
    connectionString:
        process.env.DATABASE_URL ||
        `postgresql://${process.env.POSTGRES_USER}:${process.env.POSTGRES_PASSWORD}@localhost:2345/hyd`,
});
