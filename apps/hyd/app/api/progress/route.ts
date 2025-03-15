import { NextResponse } from "next/server";
import { db } from "@/lib/db";

interface TaskProgressData {
    label: string;
    value: number;
    max_value?: number;
    status?: string;
}

export async function GET() {
    const { rows } = await db.query("SELECT id, label, value, max_value, status FROM progress;");
    return NextResponse.json(rows);
}

export async function POST(request: Request) {
    let data: TaskProgressData;
    try {
        data = (await request.json()) as TaskProgressData;
    } catch (err) {
        return new Response("Could not parse JSON body", { status: 400 });
    }
    const { label, value, max_value, status } = data;
    const existing = await db.query("SELECT id FROM progress WHERE label = $1", [label]);
    if (existing.rows.length > 0) {
        await db.query(
            "UPDATE progress SET value=$1, max_value=COALESCE($2, max_value), status=$3 WHERE label=$4",
            [value, max_value, status, label]
        );
    } else {
        await db.query(
            "INSERT INTO progress (label, value, max_value, status) VALUES ($1, $2, $3, $4)",
            [label, value, max_value, status]
        );
    }
    const { rows } = await db.query("SELECT id, label, value, max_value, status FROM progress WHERE label=$1;", [label]);
    return NextResponse.json(rows[0]);
}
