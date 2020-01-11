import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import Checkbox from "@saleor/components/Checkbox";
import Skeleton from "@saleor/components/Skeleton";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { SaleDetails_sale } from "../../types/SaleDetails";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";

export interface DiscountCollectionsProps extends ListProps, ListActions {
  discount: SaleDetails_sale | VoucherDetails_voucher;
  onCollectionAssign: () => void;
  onCollectionUnassign: (id: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    iconCell: {
      "&:last-child": {
        paddingRight: 0
      },
      width: 48 + theme.spacing.unit / 2
    },
    tableRow: {
      cursor: "pointer"
    },
    textRight: {
      textAlign: "right"
    },
    wideColumn: {
      width: "60%"
    }
  });
const DiscountCollections = withStyles(styles, {
  name: "DiscountCollections"
})(
  ({
    discount: sale,
    classes,
    disabled,
    pageInfo,
    onCollectionAssign,
    onCollectionUnassign,
    onRowClick,
    onPreviousPage,
    onNextPage,
    isChecked,
    selected,
    toggle,
    toggleAll,
    toolbar
  }: DiscountCollectionsProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle
        title={i18n.t("Eligible Collections")}
        toolbar={
          <Button color="primary" onClick={onCollectionAssign}>
            {i18n.t("Assign collections")}
          </Button>
        }
      />
      <Table>
        <TableHead
          selected={selected}
          disabled={disabled}
          items={maybe(() => sale.collections.edges.map(edge => edge.node))}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell className={classes.wideColumn}>
            {i18n.t("Collection name")}
          </TableCell>
          <TableCell className={classes.textRight}>
            {i18n.t("Products")}
          </TableCell>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={4}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            maybe(() => sale.collections.edges.map(edge => edge.node)),
            collection => {
              const isSelected = collection ? isChecked(collection.id) : false;
              return (
                <TableRow
                  selected={isSelected}
                  hover={!!collection}
                  key={collection ? collection.id : "skeleton"}
                  onClick={collection && onRowClick(collection.id)}
                  className={classes.tableRow}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(collection.id)}
                    />
                  </TableCell>
                  <TableCell>
                    {maybe<React.ReactNode>(
                      () => collection.name,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.textRight}>
                    {maybe<React.ReactNode>(
                      () => collection.products.totalCount,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.iconCell}>
                    <IconButton
                      disabled={!collection || disabled}
                      onClick={event => {
                        event.stopPropagation();
                        onCollectionUnassign(collection.id);
                      }}
                    >
                      <DeleteIcon color="primary" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={4}>
                  {i18n.t("No collections found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
DiscountCollections.displayName = "DiscountCollections";
export default DiscountCollections;
