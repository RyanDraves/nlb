import markdownStyles from "@/styles/markdown-styles.module.css";

import { MDXRemote } from 'next-mdx-remote/rsc'


type Props = {
  content: string;
};

export function PostBody({ content }: Props) {
  return (
    <div className="max-w-2xl mx-auto">
      <article className='prose prose-sm md:prose-base lg:prose-lg prose-slate !prose-invert mx-auto'>
        <MDXRemote source={content} />
        {/* <div
        className={markdownStyles["markdown"]}
        dangerouslySetInnerHTML={{ __html: content }}
      /> */}
      </article>
    </div>
  );
}
