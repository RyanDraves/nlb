import Image from "next/image";

type Props = {
    title: string;
    src: string;
    width: number;
    height: number;
};

const PostImage = ({ title, src, width, height }: Props) => {
    const image = (
        <Image
            src={src}
            alt={`Cover Image for ${title}`}
            className={"shadow-sm"}
            width={width}
            height={height}
        />
    );
    return (
        <div className="float-right ml-8 mb-4 mr-[-6rem] max-w-sm clear-right">
            {image}
        </div>
    );
};

export default PostImage;
