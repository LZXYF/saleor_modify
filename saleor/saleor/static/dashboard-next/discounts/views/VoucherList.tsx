import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { WindowTitle } from "@saleor/components/WindowTitle";
import useBulkActions from "@saleor/hooks/useBulkActions";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import usePaginator, {
  createPaginationState
} from "@saleor/hooks/usePaginator";
import useShop from "@saleor/hooks/useShop";
import { PAGINATE_BY } from "../../config";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import VoucherListPage from "../components/VoucherListPage";
import { TypedVoucherBulkDelete } from "../mutations";
import { TypedVoucherList } from "../queries";
import { VoucherBulkDelete } from "../types/VoucherBulkDelete";
import {
  voucherAddUrl,
  voucherListUrl,
  VoucherListUrlQueryParams,
  voucherUrl
} from "../urls";

interface VoucherListProps {
  params: VoucherListUrlQueryParams;
}

export const VoucherList: React.StatelessComponent<VoucherListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const shop = useShop();
  const { isSelected, listElements, reset, toggle, toggleAll } = useBulkActions(
    params.ids
  );

  const closeModal = () => navigate(voucherListUrl(), true);

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TypedVoucherList displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.vouchers.pageInfo),
          paginationState,
          params
        );

        const handleVoucherBulkDelete = (data: VoucherBulkDelete) => {
          if (data.voucherBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed vouchers")
            });
            reset();
            closeModal();
            refetch();
          }
        };

        return (
          <TypedVoucherBulkDelete onCompleted={handleVoucherBulkDelete}>
            {(voucherBulkDelete, voucherBulkDeleteOpts) => {
              const bulkRemoveTransitionState = getMutationState(
                voucherBulkDeleteOpts.called,
                voucherBulkDeleteOpts.loading,
                maybe(() => voucherBulkDeleteOpts.data.voucherBulkDelete.errors)
              );
              const onVoucherBulkDelete = () =>
                voucherBulkDelete({
                  variables: {
                    ids: params.ids
                  }
                });
              return (
                <>
                  <WindowTitle title={i18n.t("Vouchers")} />
                  <VoucherListPage
                    defaultCurrency={maybe(() => shop.defaultCurrency)}
                    vouchers={maybe(() =>
                      data.vouchers.edges.map(edge => edge.node)
                    )}
                    disabled={loading}
                    pageInfo={pageInfo}
                    onAdd={() => navigate(voucherAddUrl)}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onRowClick={id => () => navigate(voucherUrl(id))}
                    isChecked={isSelected}
                    selected={listElements.length}
                    toggle={toggle}
                    toggleAll={toggleAll}
                    toolbar={
                      <IconButton
                        color="primary"
                        onClick={() =>
                          navigate(
                            voucherListUrl({
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
                    onConfirm={onVoucherBulkDelete}
                    open={params.action === "remove"}
                    title={i18n.t("Remove Vouchers")}
                    variant="delete"
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ number }}</strong> vouchers?",
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
          </TypedVoucherBulkDelete>
        );
      }}
    </TypedVoucherList>
  );
};
export default VoucherList;
