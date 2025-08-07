import Container from '@/app/_components/container';
import Header from '@/app/_components/header';
import { PostTitle } from '@/app/_components/post-title';
import { Metadata } from 'next';
import Image from 'next/image';

export const metadata: Metadata = {
    title: 'Over the Clif - A Love Letter to Clif Bars | Ryan\'s Bizarre Blog',
    description: 'Personal reviews of every Clif bar flavor and a heartfelt poem about my love for these energy bars.',
    openGraph: {
        title: 'Over the Clif - A Love Letter to Clif Bars',
        description: 'Personal reviews of every Clif bar flavor and a heartfelt poem about my love for these energy bars.',
    },
};

interface ClifBarReview {
    name: string;
    rating: number;
    image?: string;
    review: string;
}

const clifBarReviews: ClifBarReview[] = [
    {
        name: 'Lorem Ipsum Flavor',
        rating: 4,
        image: '/assets/clif/crunchy_peanut_butter.png',
        review: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    },
    {
        name: 'Dolor Sit Amet',
        rating: 5,
        image: '/assets/clif/crunchy_peanut_butter.png',
        review: 'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'
    },
    {
        name: 'Consectetur Adipiscing',
        rating: 3.5,
        image: '/assets/clif/crunchy_peanut_butter.png',
        review: 'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.'
    },
    {
        name: 'Tempor Incididunt',
        rating: 4.5,
        image: '/assets/clif/crunchy_peanut_butter.png',
        review: 'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
    },
    {
        name: 'Ut Labore',
        rating: 4,
        image: '/assets/clif/crunchy_peanut_butter.png',
        review: 'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.'
    },
    {
        name: 'Magna Aliqua',
        rating: 3,
        image: '/assets/clif/crunchy_peanut_butter.png',
        review: 'Totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt.'
    }
];

const StarRating = ({ rating }: { rating: number }) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    return (
        <div className="flex items-center gap-1 mb-2">
            {[...Array(fullStars)].map((_, i) => (
                <span key={i} className="text-yellow-500 text-xl">★</span>
            ))}
            {hasHalfStar && <span className="text-yellow-500 text-xl">☆</span>}
            <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                {rating}/5
            </span>
        </div>
    );
};

const ClifBarReviewCard = ({ review }: { review: ClifBarReview }) => {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow duration-300 border border-gray-200 dark:border-gray-700 min-h-[200px] flex flex-col">
            {/* Header row: Title/Rating left, Image right */}
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">
                        {review.name}
                    </h3>
                    <StarRating rating={review.rating} />
                </div>
                {review.image && (
                    <div className="w-16 h-16 ml-4 rounded-md overflow-hidden flex-shrink-0">
                        <Image
                            src={review.image}
                            alt={`${review.name} Clif bar`}
                            width={64}
                            height={64}
                            className="object-cover w-full h-full"
                        />
                    </div>
                )}
            </div>

            {/* Review text spanning full width */}
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed flex-1">
                {review.review}
            </p>
        </div>
    );
};

export default function ClifPage() {
    return (
        <main>
            <Container>
                <Header />
                <article>
                    <PostTitle>Over the Clif</PostTitle>

                    <div className="prose prose-lg dark:prose-invert max-w-none mb-16">
                        <p className="text-xl leading-relaxed text-gray-700 dark:text-gray-300 mb-8">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
                            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
                            exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                        </p>
                    </div>                    {/* Reviews Section */}
                    <section className="mb-20">
                        <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-12 text-center">
                            Flavor Reviews
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {clifBarReviews.map((review, index) => (
                                <ClifBarReviewCard key={index} review={review} />
                            ))}
                        </div>
                    </section>

                    {/* Poem Section */}
                    <section className="mb-20">
                        <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-12 text-center">
                            Clif-hanger
                            <br />
                            <span className="text-lg font-normal">A short poem by Ryan Draves</span>
                        </h2>
                        <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-800 dark:to-gray-900 rounded-lg p-8 md:p-12 border border-amber-200 dark:border-gray-700">
                            <div className="prose prose-lg dark:prose-invert max-w-none">
                                <div className="font-serif italic text-lg leading-relaxed text-gray-800 dark:text-gray-200 flex justify-center">
                                    <div className="text-left space-y-6">
                                        <div className="space-y-1">
                                            <div>I embark in earnest</div>
                                            <div>to the work in person</div>
                                            <div>drawn by the reward</div>
                                            <div>of a snack I'm versed in</div>
                                        </div>

                                        <div className="space-y-1">
                                            <div>I climb these mountains</div>
                                            <div>with my trusty steed</div>
                                            <div>while I dream only</div>
                                            <div>of a Clif to feed</div>
                                        </div>

                                        <div className="space-y-1">
                                            <div>I think of bins</div>
                                            <div>could it be</div>
                                            <div>a bar so nice</div>
                                            <div>and gluten free</div>
                                        </div>

                                        <div className="space-y-1">
                                            <div>I think of the flavors</div>
                                            <div>of the possibility</div>
                                            <div>toffee, peanut, honey</div>
                                            <div>or maybe all three</div>
                                        </div>

                                        <div className="space-y-1">
                                            <div>I enter the office</div>
                                            <div>and channel my hopes</div>
                                            <div>were my efforts in vain</div>
                                            <div>biking all these slopes</div>
                                        </div>

                                        <div className="space-y-1">
                                            <div>I enter the kitchen</div>
                                            <div>a beeline to the prize</div>
                                            <div>shall I find</div>
                                            <div>this food I fantasize</div>
                                        </div>

                                        <div className="space-y-1">
                                            <div>no</div>
                                            <div>just a Nature Valley</div>
                                            <div>biscuit</div>
                                        </div>
                                    </div>
                                </div>

                                <p className="text-sm text-gray-600 dark:text-gray-400 text-center mt-8 font-sans not-italic">
                                    <em>Circa 2022</em>
                                </p>
                            </div>
                        </div>
                    </section>
                </article>
            </Container>
        </main>
    );
}
