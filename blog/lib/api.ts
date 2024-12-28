import fs from "fs";
import { join } from "path";

const postsDirectory = join(process.cwd(), "app/_posts");

export function getPostSlugs() {
  return fs.readdirSync(postsDirectory);
}
