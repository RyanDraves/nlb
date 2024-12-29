import Container from "@/app/_components/container";
import { HeroPost } from "@/app/_components/hero-post";
import { Intro } from "@/app/_components/intro";
import { MoreStories } from "@/app/_components/more-stories";
import { getPostSlugs } from "@/lib/api";
import { Post } from "@/interfaces/post"
export default async function Index() {
  const slugs = getPostSlugs();

  const allMetadatas = await Promise.all(
    slugs.map(async (slug) => {
      const { metadata } = await import(`@/app/_posts/${slug}`);
      return { ...metadata, slug: slug.replace(/\.mdx$/, "") } as Post;
    })
  );

  // "const"; what a joke language
  allMetadatas.sort((a, b) => (a.date > b.date ? -1 : 1));

  const heroPost = allMetadatas[0];

  const morePosts = allMetadatas.slice(1);

  return (
    <main>
      <Container>
        <Intro />
        <HeroPost
          title={heroPost.title}
          coverImage={heroPost.coverImage}
          date={heroPost.date}
          author={heroPost.author}
          slug={heroPost.slug}
          excerpt={heroPost.excerpt}
        />
        {morePosts.length > 0 && <MoreStories posts={morePosts} />}
      </Container>
    </main>
  );
}
