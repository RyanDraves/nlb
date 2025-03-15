import { Pool } from "pg";
import fs from 'fs';

let password = process.env.POSTGRES_PASSWORD;
if (process.env.POSTGRES_PASSWORD_FILE) {
    try {
        password = fs.readFileSync(process.env.POSTGRES_PASSWORD_FILE, 'utf8').trim();
    } catch (err) {
        console.error(`Error reading POSTGRES_PASSWORD_FILE: ${err}`);
    }
}

let user = process.env.POSTGRES_USER || 'hyd';
let host = process.env.POSTGRES_HOST || 'localhost';
let port = process.env.POSTGRES_PORT || 5432;
let database = process.env.POSTGRES_DB || 'hyd';

export const db = new Pool({
    connectionString:
        process.env.DATABASE_URL ||
        `postgresql://${user}:${password}@${host}:${port}/${database}`,
});
