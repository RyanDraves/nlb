import { Post } from "@/interfaces/post";

// TODO: This doesn't work or provide any type safety
declare module "*.mdx" {
    // Named export for "metadata"
    export const metadata: Post;

    // Default export for the MDX component
    const MDXPage: (props: any) => JSX.Element;
    export default MDXPage;
}
