// The global the widget bundle (widget/src/index.ts) installs.
interface DocsChatWidget {
  destroy(): void;
  open(focus?: boolean): void;
}

interface DocsChatApi {
  mount(options: {
    api?: string;
    bot?: string;
    document?: string;
    position?: "right" | "left";
    open?: boolean;
    overrides?: Record<string, unknown>;
  }): DocsChatWidget;
  open(): void;
  destroyAll(): void;
}

interface Window {
  DocsChat?: DocsChatApi;
}
