type Props = {
  children: React.ReactNode;
};

export function PostBody({ children }: Props) {
  return (
    <div className="max-w-2xl mx-auto">
      {/* TODO: Made work with theme switcher */}
      {/* Look at https://nextjs.org/docs/pages/building-your-application/configuring/mdx#using-tailwind-typography-plugin */}
      <article className='prose prose-sm md:prose-base lg:prose-lg prose-slate !prose-invert mx-auto'>
        {children}
      </article>
    </div>
  );
}
