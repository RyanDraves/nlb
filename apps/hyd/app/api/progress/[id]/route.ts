import { db } from "@/lib/db";

export async function DELETE(
    request: Request,
    { params }: { params: { id: string } }
) {
    const { id } = await params;
    await db.query("DELETE FROM progress WHERE id = $1", [id]);
    return new Response("OK", { status: 200 });
}
