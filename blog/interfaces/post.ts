import { type Author } from "./author";

// Metadata for a blog post
// Each `.mdx` post should export a `metadata` object with these properties,
// except for `slug` which is derived from the filename.
export type Post = {
  slug: string;
  title: string;
  date: string;
  coverImage: string;
  author: Author;
  excerpt: string;
  ogImage: {
    url: string;
  };
  content: string;
};
