interface Props {
    videoId: string
    videoTitle: string
}

export default function YoutubeVideo(props: Props) {
    return (
        <iframe width="640" height="390"
            src={`https://www.youtube.com/embed/${props.videoId}`} title={props.videoTitle}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        ></iframe>
    );
}
