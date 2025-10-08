"use client";

import Image from "next/image";
import { useState } from "react";

type Props = {
    title: string;
    src: string;
    width: number;
    height: number;
    enlargeable?: boolean;
};

const PostImage = ({ title, src, width, height, enlargeable = false }: Props) => {
    const [isEnlarged, setIsEnlarged] = useState(false);

    const image = (
        <Image
            src={src}
            alt={`Image for ${title}`}
            className={`shadow-sm ${enlargeable ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}`}
            width={width}
            height={height}
            onClick={enlargeable ? () => setIsEnlarged(true) : undefined}
        />
    );

    return (
        <>
            <div className="float-right ml-8 mb-4 mr-[-6rem] max-w-sm clear-right relative z-10">
                {image}
            </div>

            {/* Modal for enlarged image */}
            {enlargeable && isEnlarged && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
                    onClick={() => setIsEnlarged(false)}
                >
                    <div className="relative max-w-[90vw] max-h-[90vh]">
                        <Image
                            src={src}
                            alt={`Enlarged ${title}`}
                            className="shadow-lg max-w-full max-h-full object-contain"
                            width={width * 2} // Double the size for the enlarged view
                            height={height * 2}
                            onClick={(e: React.MouseEvent) => e.stopPropagation()} // Prevent closing when clicking the image
                        />
                        <button
                            className="absolute top-4 right-4 text-white text-4xl font-bold hover:text-gray-300 transition-colors"
                            style={{ textShadow: '1px 1px 0 black, -1px -1px 0 black, 1px -1px 0 black, -1px 1px 0 black' }}
                            onClick={() => setIsEnlarged(false)}
                            aria-label="Close enlarged image"
                        >
                            ×
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default PostImage;
