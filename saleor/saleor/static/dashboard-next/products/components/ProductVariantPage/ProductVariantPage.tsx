import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { ProductVariant } from "../../types/ProductVariant";
import ProductVariantAttributes from "../ProductVariantAttributes";
import ProductVariantImages from "../ProductVariantImages";
import ProductVariantImageSelectDialog from "../ProductVariantImageSelectDialog";
import ProductVariantNavigation from "../ProductVariantNavigation";
import ProductVariantPrice from "../ProductVariantPrice";
import ProductVariantStock from "../ProductVariantStock";

interface ProductVariantPageProps {
  variant?: ProductVariant;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  loading?: boolean;
  placeholderImage?: string;
  header: string;
  onAdd();
  onBack();
  onDelete();
  onSubmit(data: any);
  onImageSelect(id: string);
  onVariantClick(variantId: string);
}

const ProductVariantPage: React.StatelessComponent<ProductVariantPageProps> = ({
  errors: formErrors,
  loading,
  header,
  placeholderImage,
  saveButtonBarState,
  variant,
  onAdd,
  onBack,
  onDelete,
  onImageSelect,
  onSubmit,
  onVariantClick
}) => {
  const [isModalOpened, setModalStatus] = React.useState(false);
  const toggleModal = () => setModalStatus(!isModalOpened);

  const variantImages = variant ? variant.images.map(image => image.id) : [];
  const productImages = variant
    ? variant.product.images.sort((prev, next) =>
        prev.sortOrder > next.sortOrder ? 1 : -1
      )
    : undefined;
  const images = productImages
    ? productImages
        .filter(image => variantImages.indexOf(image.id) !== -1)
        .sort((prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1))
    : undefined;
  return (
    <>
      <Container>
        <AppHeader onBack={onBack}>
          {maybe(() => variant.product.name)}
        </AppHeader>
        <PageHeader title={header} />
        <Form
          initial={{
            attributes: maybe(
              () =>
                variant.attributes.map(a => ({
                  name: a.attribute.name,
                  slug: a.attribute.slug,
                  value: a.value.slug
                })),
              []
            ),
            costPrice:
              variant && variant.costPrice
                ? variant.costPrice.amount.toString()
                : null,
            priceOverride:
              variant && variant.priceOverride
                ? variant.priceOverride.amount.toString()
                : null,
            quantity: variant && variant.quantity ? variant.quantity : "",
            sku: variant && variant.sku
          }}
          errors={formErrors}
          onSubmit={onSubmit}
          confirmLeave
        >
          {({ change, data, errors, hasChanged, submit }) => (
            <>
              <Grid variant="inverted">
                <div>
                  <ProductVariantNavigation
                    current={variant ? variant.id : undefined}
                    fallbackThumbnail={maybe(
                      () => variant.product.thumbnail.url
                    )}
                    variants={maybe(() => variant.product.variants)}
                    onAdd={onAdd}
                    onRowClick={(variantId: string) => {
                      if (variant) {
                        return onVariantClick(variantId);
                      }
                    }}
                  />
                </div>
                <div>
                  <ProductVariantAttributes
                    attributes={
                      variant && variant.attributes
                        ? variant.attributes.map(a => a.attribute)
                        : undefined
                    }
                    data={data}
                    disabled={loading}
                    onChange={change}
                  />
                  <CardSpacer />
                  <ProductVariantImages
                    disabled={loading}
                    images={images}
                    placeholderImage={placeholderImage}
                    onImageAdd={toggleModal}
                  />
                  <CardSpacer />
                  <ProductVariantPrice
                    errors={errors}
                    priceOverride={data.priceOverride}
                    currencySymbol={
                      variant && variant.priceOverride
                        ? variant.priceOverride.currency
                        : variant && variant.costPrice
                        ? variant.costPrice.currency
                        : ""
                    }
                    costPrice={data.costPrice}
                    loading={loading}
                    onChange={change}
                  />
                  <CardSpacer />
                  <ProductVariantStock
                    errors={errors}
                    sku={data.sku}
                    quantity={data.quantity}
                    stockAllocated={
                      variant ? variant.quantityAllocated : undefined
                    }
                    loading={loading}
                    onChange={change}
                  />
                </div>
              </Grid>
              <SaveButtonBar
                disabled={loading || !hasChanged}
                state={saveButtonBarState}
                onCancel={onBack}
                onDelete={onDelete}
                onSave={submit}
              />
            </>
          )}
        </Form>
      </Container>
      {variant && (
        <ProductVariantImageSelectDialog
          onClose={toggleModal}
          onImageSelect={onImageSelect}
          open={isModalOpened}
          images={productImages}
          selectedImages={maybe(() => variant.images.map(image => image.id))}
        />
      )}
    </>
  );
};
ProductVariantPage.displayName = "ProductVariantPage";
export default ProductVariantPage;
