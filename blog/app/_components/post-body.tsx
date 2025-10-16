type Props = {
  children: React.ReactNode;
};

export function PostBody({ children }: Props) {
  return (
    <div className="max-w-5xl mx-auto px-12">
      <article className='prose prose-sm md:prose-base lg:prose-lg prose-slate dark:prose-invert mx-auto max-w-3xl'>
        {children}
        {/* Make sure floating elements are cleared */}
        <div className="clear-both"></div>
      </article>
    </div>
  );
}
