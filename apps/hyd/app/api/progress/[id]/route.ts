import { db } from "@/lib/db";

interface DeleteParams {
    id: string;
}


export async function DELETE(
    request: Request,
    { params }: { params: Promise<DeleteParams> }
) {
    const { id } = await params;
    await db.query("DELETE FROM progress WHERE id = $1", [id]);
    return new Response("OK", { status: 200 });
}
