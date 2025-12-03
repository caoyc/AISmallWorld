/// <reference types="vite/client" />

declare module 'dompurify' {
  interface Config {
    ALLOWED_TAGS?: string[]
    ALLOWED_ATTR?: string[]
  }
  
  interface DOMPurify {
    sanitize(dirty: string, config?: Config): string
  }
  
  function createDOMPurify(window?: Window): DOMPurify
  export default createDOMPurify
}
