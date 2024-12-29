import Container from "@/app/_components/container";
import Header from "@/app/_components/header";
import { PostBody } from "@/app/_components/post-body";
import { PostHeader } from "@/app/_components/post-header";
import { Post } from "@/interfaces/post";

export default function MdxLayout({ children, metadata }: { children: React.ReactNode, metadata: Post }) {
    return <main>
        <Container>
            <Header />
            <article className="mb-32">
                <PostHeader
                    title={metadata.title}
                    coverImage={metadata.coverImage}
                    date={metadata.date}
                    author={metadata.author}
                />
                <PostBody children={children} />
            </article>
        </Container>
    </main>
}
