import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import { ControlledCheckbox } from "@saleor/components/ControlledCheckbox";
import Form from "@saleor/components/Form";
import i18n from "../../../i18n";

export interface FormData {
  restock: boolean;
}

const styles = (theme: Theme) =>
  createStyles({
    deleteButton: {
      "&:hover": {
        backgroundColor: theme.palette.error.main
      },
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText
    }
  });

interface OrderFulfillmentCancelDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  onClose();
  onConfirm(data: FormData);
}

const OrderFulfillmentCancelDialog = withStyles(styles, {
  name: "OrderFulfillmentCancelDialog"
})(
  ({
    confirmButtonState,
    classes,
    open,
    onConfirm,
    onClose
  }: OrderFulfillmentCancelDialogProps) => (
    <Dialog onClose={onClose} open={open}>
      <Form initial={{ restock: true }} onSubmit={onConfirm}>
        {({ change, data, submit }) => (
          <>
            <DialogTitle>
              {i18n.t("Cancel fulfillment", { context: "title" })}
            </DialogTitle>
            <DialogContent>
              <DialogContentText>
                {i18n.t("Are you sure you want to cancel this fulfillment?")}
              </DialogContentText>
              <ControlledCheckbox
                checked={data.restock}
                label={i18n.t("Restock items?")}
                name="restock"
                onChange={change}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={onClose}>
                {i18n.t("Back", { context: "button" })}
              </Button>
              <ConfirmButton
                transitionState={confirmButtonState}
                className={classes.deleteButton}
                variant="contained"
                onClick={submit}
              >
                {i18n.t("Cancel fulfillment", { context: "button" })}
              </ConfirmButton>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  )
);
OrderFulfillmentCancelDialog.displayName = "OrderFulfillmentCancelDialog";
export default OrderFulfillmentCancelDialog;
