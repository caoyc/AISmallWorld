declare module 'marked' {
  export interface MarkedOptions {
    breaks?: boolean
    gfm?: boolean
    headerIds?: boolean
    mangle?: boolean
  }
  
  export class Marked {
    setOptions(options: MarkedOptions): void
    parse(markdown: string): string
  }
  
  const marked: Marked
  export default marked
  export { marked }
}

