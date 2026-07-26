"use client";

import { useEffect, useState } from "react";

const MAX_IMAGES = 5;

export function ReferenceImagePicker({
  onChange,
}: {
  onChange: (files: File[]) => void;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);

  useEffect(() => {
    const urls = files.map((f) => URL.createObjectURL(f));
    setPreviews(urls);
    return () => urls.forEach((u) => URL.revokeObjectURL(u));
  }, [files]);

  function handleSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(e.target.files ?? []);
    const next = [...files, ...picked].slice(0, MAX_IMAGES);
    setFiles(next);
    onChange(next);
    e.target.value = "";
  }

  function remove(index: number) {
    const next = files.filter((_, i) => i !== index);
    setFiles(next);
    onChange(next);
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        {previews.map((src, i) => (
          <div
            key={i}
            className="relative h-16 w-16 overflow-hidden rounded-lg border border-crust-200"
          >
            <img src={src} alt="" className="h-full w-full object-cover" />
            <button
              type="button"
              onClick={() => remove(i)}
              aria-label="Remove image"
              className="absolute right-0 top-0 flex h-4 w-4 items-center justify-center rounded-bl bg-black/60 text-[10px] text-white"
            >
              ✕
            </button>
          </div>
        ))}
        {files.length < MAX_IMAGES && (
          <label className="flex h-16 w-16 cursor-pointer items-center justify-center rounded-lg border border-dashed border-crust-300 text-xs text-crust-500">
            + Add
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handleSelect}
            />
          </label>
        )}
      </div>
      <p className="mt-2 text-xs text-amber-600">
        Reference images are previewed locally only — they won't be attached to
        your order yet. Image upload isn't connected to the backend for custom
        orders in this build; describe what you're picturing in the message
        field below in the meantime.
      </p>
    </div>
  );
}
