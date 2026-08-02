"use client";

import { useState } from "react";
import Image from "next/image";
import {
  useUploadProductImagesMutation,
  useDeleteProductImageMutation,
} from "@/store/api/adminProductsApi";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn } from "@/lib/utils";
import type { ProductImage } from "@/types/api";

export function ProductImageUploader({
  productId,
  images,
}: {
  productId: string;
  images: ProductImage[];
}) {
  const [uploadImages, { isLoading: isUploading }] =
    useUploadProductImagesMutation();
  const [deleteImage] = useDeleteProductImageMutation();
  const [isDragging, setIsDragging] = useState(false);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    await uploadImages({ id: productId, files: Array.from(files) });
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-sm",
          isDragging
            ? "border-crust-500 bg-crust-50"
            : "border-crust-200 text-crust-500",
        )}
      >
        {isUploading ? (
          <LoadingSpinner />
        ) : (
          <>
            <p>Drag and drop images here, or</p>
            <label className="mt-1 cursor-pointer text-crust-700 underline">
              browse files
              <input
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
              />
            </label>
          </>
        )}
      </div>

      {images.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {images.map((img) => (
            <div
              key={img.id}
              className="relative h-20 w-20 overflow-hidden rounded-lg border border-crust-100"
            >
              <Image
                src={img.url}
                alt={img.alt}
                fill
                className="object-cover"
              />
              <button
                type="button"
                onClick={() => deleteImage({ productId, imageId: img.id })}
                aria-label="Delete image"
                className="absolute right-0 top-0 flex h-5 w-5 items-center justify-center rounded-bl bg-black/60 text-xs text-white"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
