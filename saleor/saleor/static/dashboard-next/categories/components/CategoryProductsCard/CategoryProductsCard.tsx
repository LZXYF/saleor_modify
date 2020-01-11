import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import ProductList from "@saleor/components/ProductList";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import { CategoryDetails_category_products_edges_node } from "../../types/CategoryDetails";

interface CategoryProductsCardProps extends PageListProps, ListActions {
  products: CategoryDetails_category_products_edges_node[];
  categoryName: string;
}

export const CategoryProductsCard: React.StatelessComponent<
  CategoryProductsCardProps
> = ({
  products,
  disabled,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick,
  categoryName,
  isChecked,
  selected,
  toggle,
  toggleAll,
  toolbar
}) => (
  <Card>
    <CardTitle
      title={i18n.t("Products in {{ categoryName }}", { categoryName })}
      toolbar={
        <Button color="primary" variant="text" onClick={onAdd}>
          {i18n.t("Add product")}
        </Button>
      }
    />
    <ProductList
      products={products}
      disabled={disabled}
      pageInfo={pageInfo}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
      selected={selected}
      isChecked={isChecked}
      toggle={toggle}
      toggleAll={toggleAll}
      toolbar={toolbar}
    />
  </Card>
);

CategoryProductsCard.displayName = "CategoryProductsCard";
export default CategoryProductsCard;
