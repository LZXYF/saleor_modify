import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import useBulkActions from "@saleor/hooks/useBulkActions";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import usePaginator, {
  createPaginationState
} from "@saleor/hooks/usePaginator";
import { PAGINATE_BY } from "../../config";
import { configurationMenuUrl } from "../../configuration";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import ProductTypeListPage from "../components/ProductTypeListPage";
import { TypedProductTypeBulkDeleteMutation } from "../mutations";
import { TypedProductTypeListQuery } from "../queries";
import { ProductTypeBulkDelete } from "../types/ProductTypeBulkDelete";
import {
  productTypeAddUrl,
  productTypeListUrl,
  ProductTypeListUrlQueryParams,
  productTypeUrl
} from "../urls";

interface ProductTypeListProps {
  params: ProductTypeListUrlQueryParams;
}

export const ProductTypeList: React.StatelessComponent<
  ProductTypeListProps
> = ({ params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { isSelected, listElements, reset, toggle, toggleAll } = useBulkActions(
    params.ids
  );

  const closeModal = () => navigate(productTypeListUrl(), true);

  const paginationState = createPaginationState(PAGINATE_BY, params);
  return (
    <TypedProductTypeListQuery displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.productTypes.pageInfo),
          paginationState,
          params
        );

        const handleProductTypeBulkDelete = (data: ProductTypeBulkDelete) => {
          if (data.productTypeBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed product types")
            });
            reset();
            refetch();
            navigate(
              productTypeListUrl({
                ...params,
                action: undefined,
                ids: undefined
              })
            );
          }
        };

        return (
          <TypedProductTypeBulkDeleteMutation
            onCompleted={handleProductTypeBulkDelete}
          >
            {(productTypeBulkDelete, productTypeBulkDeleteOpts) => {
              const bulkRemoveTransitionState = getMutationState(
                productTypeBulkDeleteOpts.called,
                productTypeBulkDeleteOpts.loading,
                maybe(
                  () =>
                    productTypeBulkDeleteOpts.data.productTypeBulkDelete.errors
                )
              );

              const onProductTypeBulkDelete = () =>
                productTypeBulkDelete({
                  variables: {
                    ids: params.ids
                  }
                });
              return (
                <>
                  <ProductTypeListPage
                    disabled={loading}
                    productTypes={maybe(() =>
                      data.productTypes.edges.map(edge => edge.node)
                    )}
                    pageInfo={pageInfo}
                    onAdd={() => navigate(productTypeAddUrl)}
                    onBack={() => navigate(configurationMenuUrl)}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onRowClick={id => () => navigate(productTypeUrl(id))}
                    isChecked={isSelected}
                    selected={listElements.length}
                    toggle={toggle}
                    toggleAll={toggleAll}
                    toolbar={
                      <IconButton
                        color="primary"
                        onClick={() =>
                          navigate(
                            productTypeListUrl({
                              action: "remove",
                              ids: listElements
                            })
                          )
                        }
                      >
                        <DeleteIcon />
                      </IconButton>
                    }
                  />
                  <ActionDialog
                    confirmButtonState={bulkRemoveTransitionState}
                    onClose={closeModal}
                    onConfirm={onProductTypeBulkDelete}
                    open={params.action === "remove"}
                    title={i18n.t("Remove Product Types")}
                    variant="delete"
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ number }}</strong> product types?",
                          {
                            number: maybe(
                              () => params.ids.length.toString(),
                              "..."
                            )
                          }
                        )
                      }}
                    />
                  </ActionDialog>
                </>
              );
            }}
          </TypedProductTypeBulkDeleteMutation>
        );
      }}
    </TypedProductTypeListQuery>
  );
};
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
