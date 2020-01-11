import { RawDraftContentState } from "draft-js";
import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import { CardSpacer } from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import SeoForm from "@saleor/components/SeoForm";
import { Tab, TabContainer } from "@saleor/components/Tab";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { TabListActions, UserError } from "../../../types";
import CategoryDetailsForm from "../../components/CategoryDetailsForm";
import CategoryList from "../../components/CategoryList";
import {
  CategoryDetails_category,
  CategoryDetails_category_children_edges_node,
  CategoryDetails_category_products_edges_node
} from "../../types/CategoryDetails";
import CategoryBackground from "../CategoryBackground";
import CategoryProductsCard from "../CategoryProductsCard";

export interface FormData {
  backgroundImageAlt: string;
  description: RawDraftContentState;
  name: string;
  seoTitle: string;
  seoDescription: string;
}

export enum CategoryPageTab {
  categories = "categories",
  products = "products"
}

export interface CategoryUpdatePageProps
  extends TabListActions<"productListToolbar" | "subcategoryListToolbar"> {
  changeTab: (index: CategoryPageTab) => void;
  currentTab: CategoryPageTab;
  errors: UserError[];
  disabled: boolean;
  category: CategoryDetails_category;
  products: CategoryDetails_category_products_edges_node[];
  subcategories: CategoryDetails_category_children_edges_node[];
  pageInfo: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  saveButtonBarState: ConfirmButtonTransitionState;
  onImageDelete: () => void;
  onSubmit: (data: FormData) => void;
  onImageUpload(file: File);
  onNextPage();
  onPreviousPage();
  onProductClick(id: string): () => void;
  onAddProduct();
  onBack();
  onDelete();
  onAddCategory();
  onCategoryClick(id: string): () => void;
}

const CategoriesTab = Tab(CategoryPageTab.categories);
const ProductsTab = Tab(CategoryPageTab.products);

export const CategoryUpdatePage: React.StatelessComponent<
  CategoryUpdatePageProps
> = ({
  changeTab,
  currentTab,
  category,
  disabled,
  errors: userErrors,
  pageInfo,
  products,
  saveButtonBarState,
  subcategories,
  onAddCategory,
  onAddProduct,
  onBack,
  onCategoryClick,
  onDelete,
  onNextPage,
  onPreviousPage,
  onProductClick,
  onSubmit,
  onImageDelete,
  onImageUpload,
  isChecked,
  productListToolbar,
  selected,
  subcategoryListToolbar,
  toggle,
  toggleAll
}: CategoryUpdatePageProps) => {
  const initialData: FormData = category
    ? {
        backgroundImageAlt: maybe(() => category.backgroundImage.alt, ""),
        description: maybe(() => JSON.parse(category.descriptionJson)),
        name: category.name || "",
        seoDescription: category.seoDescription || "",
        seoTitle: category.seoTitle || ""
      }
    : {
        backgroundImageAlt: "",
        description: "",
        name: "",
        seoDescription: "",
        seoTitle: ""
      };
  return (
    <Form
      onSubmit={onSubmit}
      initial={initialData}
      errors={userErrors}
      confirmLeave
    >
      {({ data, change, errors, submit, hasChanged }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Categories")}</AppHeader>
          <PageHeader title={category ? category.name : undefined} />
          <CategoryDetailsForm
            category={category}
            data={data}
            disabled={disabled}
            errors={errors}
            onChange={change}
          />
          <CardSpacer />
          <CategoryBackground
            data={data}
            onImageUpload={onImageUpload}
            onImageDelete={onImageDelete}
            image={maybe(() => category.backgroundImage)}
            onChange={change}
          />
          <CardSpacer />
          <SeoForm
            helperText={i18n.t(
              "Add search engine title and description to make this category easier to find"
            )}
            title={data.seoTitle}
            titlePlaceholder={data.name}
            description={data.seoDescription}
            descriptionPlaceholder={data.name}
            loading={!category}
            onChange={change}
            disabled={disabled}
          />
          <CardSpacer />
          <TabContainer>
            <CategoriesTab
              isActive={currentTab === CategoryPageTab.categories}
              changeTab={changeTab}
            >
              {i18n.t("Subcategories")}
            </CategoriesTab>
            <ProductsTab
              isActive={currentTab === CategoryPageTab.products}
              changeTab={changeTab}
            >
              {i18n.t("Products")}
            </ProductsTab>
          </TabContainer>
          <CardSpacer />
          {currentTab === CategoryPageTab.categories && (
            <CategoryList
              disabled={disabled}
              isRoot={false}
              categories={subcategories}
              onAdd={onAddCategory}
              onRowClick={onCategoryClick}
              onNextPage={onNextPage}
              onPreviousPage={onPreviousPage}
              pageInfo={pageInfo}
              toggle={toggle}
              toggleAll={toggleAll}
              selected={selected}
              isChecked={isChecked}
              toolbar={subcategoryListToolbar}
            />
          )}
          {currentTab === CategoryPageTab.products && (
            <CategoryProductsCard
              categoryName={maybe(() => category.name)}
              products={products}
              disabled={disabled}
              pageInfo={pageInfo}
              onNextPage={onNextPage}
              onPreviousPage={onPreviousPage}
              onRowClick={onProductClick}
              onAdd={onAddProduct}
              toggle={toggle}
              toggleAll={toggleAll}
              selected={selected}
              isChecked={isChecked}
              toolbar={productListToolbar}
            />
          )}
          <SaveButtonBar
            onCancel={onBack}
            onDelete={onDelete}
            onSave={submit}
            labels={{
              delete: i18n.t("Delete category")
            }}
            state={saveButtonBarState}
            disabled={disabled || !hasChanged}
          />
        </Container>
      )}
    </Form>
  );
};
CategoryUpdatePage.displayName = "CategoryUpdatePage";
export default CategoryUpdatePage;
