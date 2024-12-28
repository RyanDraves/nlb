import type { BundledLanguage } from 'shiki'
import { codeToHtml } from 'shiki'

interface Props {
    children: string
    lang: BundledLanguage
    name: string
}

export default async function CodeBlock(props: Props) {
    const out = await codeToHtml(props.children, {
        lang: props.lang,
        theme: 'github-dark'
    })

    return (
        <div className="relative max-w-full mb-3">
            <div className="mx-1 bg-gray-800 text-gray-100 px-3 py-1 text-sm font-mono inline-block rounded-t-md border border-b-0 border-gray-700">
                {props.name}
            </div>
            <div className="rounded-b-md overflow-auto">
                <div className="p-0 [&_pre]:m-0 [&_pre]:border-0 [&_pre]p-0" dangerouslySetInnerHTML={{ __html: out }} />
            </div>
        </div>
    );
}
