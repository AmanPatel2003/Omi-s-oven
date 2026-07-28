"use client";

import { useEffect, useState } from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import {
  useGetAdminCategoriesQuery,
  useCreateAdminCategoryMutation,
  useDeleteAdminCategoryMutation,
  useReorderCategoriesMutation,
} from "@/store/api/adminCategoriesApi";
import { SortableCategoryRow } from "@/components/admin/SortableCategoryRow";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { AdminCategory } from "@/types/api";

function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

export default function AdminCategoriesPage() {
  const { data, isLoading } = useGetAdminCategoriesQuery();
  const [createCategory, { isLoading: isCreating }] =
    useCreateAdminCategoryMutation();
  const [deleteCategory, { isLoading: isDeleting }] =
    useDeleteAdminCategoryMutation();
  const [reorderCategories] = useReorderCategoriesMutation();

  const [localOrder, setLocalOrder] = useState<AdminCategory[]>([]);
  const [newName, setNewName] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<AdminCategory | null>(null);

  useEffect(() => {
    if (data) setLocalOrder([...data].sort((a, b) => a.order - b.order));
  }, [data]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = localOrder.findIndex((c) => c.id === active.id);
    const newIndex = localOrder.findIndex((c) => c.id === over.id);
    const reordered = arrayMove(localOrder, oldIndex, newIndex);
    setLocalOrder(reordered);
    reorderCategories(reordered.map((c) => c.id));
  }

  async function handleAdd() {
    if (!newName.trim()) return;
    await createCategory({ name: newName, slug: slugify(newName) });
    setNewName("");
  }

  async function handleConfirmDelete() {
    if (!deleteTarget) return;
    await deleteCategory(deleteTarget.id);
    setDeleteTarget(null);
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Categories
      </h1>
      <p className="mt-1 text-sm text-crust-500">Drag the handle to reorder.</p>

      <div className="mt-4 flex gap-2">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New category name"
          className="flex-1 rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
        <Button
          className="w-auto px-4"
          isLoading={isCreating}
          onClick={handleAdd}
        >
          Add
        </Button>
      </div>

      <div className="mt-6">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={localOrder.map((c) => c.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="flex flex-col gap-2">
              {localOrder.map((category) => (
                <SortableCategoryRow
                  key={category.id}
                  category={category}
                  onDeleteClick={setDeleteTarget}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      {deleteTarget && (
        <ConfirmDialog
          title={`Delete "${deleteTarget.name}"?`}
          isDangerous
          isLoading={isDeleting}
          confirmLabel="Delete"
          description={
            deleteTarget.productCount > 0 ? (
              <>
                This category has{" "}
                <strong>{deleteTarget.productCount} product(s)</strong> linked
                to it. It will be <strong>soft-deleted</strong> — hidden from
                shoppers but kept in the system so those products aren't left
                without a category — rather than permanently removed.
              </>
            ) : (
              <>
                This category has no products linked to it and will be{" "}
                <strong>permanently deleted</strong>. This can't be undone.
              </>
            )
          }
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
