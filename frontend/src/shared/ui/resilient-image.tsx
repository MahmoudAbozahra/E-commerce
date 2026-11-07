"use client";

import Image, { type ImageProps } from "next/image";
import { useState } from "react";

type Props = ImageProps & { fallbackLabel: string };

export function ResilientImage({ fallbackLabel, onError, alt, ...props }: Props) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div className="absolute inset-0 grid place-items-center bg-mist/60 px-4 text-center text-xs text-ink/45" data-image-fallback role="img" aria-label={fallbackLabel}>
        <span>Image temporarily unavailable</span>
      </div>
    );
  }
  return (
    <Image
      {...props}
      alt={alt}
      data-product-image
      onError={(event) => {
        if (process.env.NODE_ENV === "development") console.warn("Product image failed to load", props.src);
        setFailed(true);
        onError?.(event);
      }}
    />
  );
}
