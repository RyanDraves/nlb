import { Metadata } from "next";
import { getPostSlugs } from "@/lib/api";
import { Post as PostInferface } from "@/interfaces/post";


export default async function Post(props: Params) {
    const slug = (await props.params).slug;
    const { default: MDXPage } = await import(`@/app/_posts/${slug}.mdx`);

    return (
        <MDXPage />
    );
}

type Params = {
    params: Promise<{
        slug: string;
    }>;
};

export async function generateMetadata(props: Params): Promise<Metadata> {
    const slug = (await props.params).slug;
    const { metadata }: { metadata: PostInferface } = await import(`@/app/_posts/${slug}.mdx`);

    const title = metadata.title;

    return {
        title,
        openGraph: {
            title,
            images: [metadata.ogImage.url],
        },
    };
}

export async function generateStaticParams() {
    const slugs = getPostSlugs();

    return slugs.map((slug) => ({
        slug: slug.replace(/\.mdx$/, ""),
    }));
}



export const dynamicParams = false;
