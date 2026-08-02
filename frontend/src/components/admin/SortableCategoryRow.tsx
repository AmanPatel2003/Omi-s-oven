"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useUpdateAdminCategoryMutation } from "@/store/api/adminCategoriesApi";
import type { AdminCategory } from "@/types/api";

export function SortableCategoryRow({
  category,
  onDeleteClick,
}: {
  category: AdminCategory;
  onDeleteClick: (category: AdminCategory) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: category.id,
  });
  const [updateCategory] = useUpdateAdminCategoryMutation();
  const [isEditing, setIsEditing] = useState(false);
  const [nameDraft, setNameDraft] = useState(category.name);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  async function saveEdit() {
    if (nameDraft.trim() && nameDraft !== category.name) {
      await updateCategory({
        id: category.id,
        name: nameDraft,
        slug: category.slug,
      });
    }
    setIsEditing(false);
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-3 rounded-xl border border-crust-100 bg-white p-3"
    >
      <button
        type="button"
        {...attributes}
        {...listeners}
        aria-label="Drag to reorder"
        className="cursor-grab text-crust-300"
      >
        ⠿
      </button>

      {isEditing ? (
        <input
          autoFocus
          value={nameDraft}
          onChange={(e) => setNameDraft(e.target.value)}
          onBlur={saveEdit}
          onKeyDown={(e) => e.key === "Enter" && saveEdit()}
          className="flex-1 rounded-lg border border-crust-200 px-2 py-1 text-sm"
        />
      ) : (
        <span className="flex-1 text-sm text-crust-800">{category.name}</span>
      )}

      <span className="text-xs text-crust-400">
        {category.productCount} products
      </span>

      <button
        type="button"
        onClick={() => setIsEditing(true)}
        className="text-xs text-crust-600 underline"
      >
        Rename
      </button>
      <button
        type="button"
        onClick={() => onDeleteClick(category)}
        className="text-xs text-red-600 underline"
      >
        Delete
      </button>
    </div>
  );
}
