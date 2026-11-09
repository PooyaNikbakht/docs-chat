// Load the same widget bundle the embed snippet uses, for pages that mount it from code.
type DocsChat = NonNullable<Window["DocsChat"]>;

let loading: Promise<DocsChat> | null = null;

export function loadWidget(): Promise<DocsChat> {
  if (window.DocsChat) return Promise.resolve(window.DocsChat);
  if (!loading) {
    loading = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "/embed/widget.js";
      script.async = true;
      script.onload = () => (window.DocsChat ? resolve(window.DocsChat) : reject(new Error("Widget failed to start")));
      script.onerror = () => {
        loading = null;
        reject(new Error("Couldn't load the chat widget."));
      };
      document.head.appendChild(script);
    });
  }
  return loading;
}
