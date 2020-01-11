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
import StatusLabel from "@saleor/components/StatusLabel";
import TableCellAvatar from "@saleor/components/TableCellAvatar";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { SaleDetails_sale } from "../../types/SaleDetails";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";

export interface SaleProductsProps extends ListProps, ListActions {
  discount: SaleDetails_sale | VoucherDetails_voucher;
  onProductAssign: () => void;
  onProductUnassign: (id: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colName: {},
      colPublished: {
        width: 150
      },
      colType: {
        width: 200
      }
    },
    colName: {},
    colPublished: {},
    colType: {},
    iconCell: {
      "&:last-child": {
        paddingRight: 0
      },
      width: 48 + theme.spacing.unit / 2
    },
    tableRow: {
      cursor: "pointer"
    }
  });
const DiscountProducts = withStyles(styles, {
  name: "DiscountProducts"
})(
  ({
    discount: sale,
    classes,
    disabled,
    pageInfo,
    onRowClick,
    onPreviousPage,
    onProductAssign,
    onProductUnassign,
    onNextPage,
    isChecked,
    selected,
    toggle,
    toggleAll,
    toolbar
  }: SaleProductsProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle
        title={i18n.t("Eligible Products")}
        toolbar={
          <Button color="primary" onClick={onProductAssign}>
            {i18n.t("Assign products")}
          </Button>
        }
      />
      <Table>
        <TableHead
          selected={selected}
          disabled={disabled}
          items={maybe(() => sale.products.edges.map(edge => edge.node))}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell />
          <TableCell />
          <TableCell className={classes.colName}>
            {i18n.t("Product name")}
          </TableCell>
          <TableCell className={classes.colType}>
            {i18n.t("Product Type")}
          </TableCell>
          <TableCell className={classes.colPublished}>
            {i18n.t("Published")}
          </TableCell>
          <TableCell />
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={6}
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
            maybe(() => sale.products.edges.map(edge => edge.node)),
            product => {
              const isSelected = product ? isChecked(product.id) : false;
              return (
                <TableRow
                  hover={!!product}
                  key={product ? product.id : "skeleton"}
                  onClick={product && onRowClick(product.id)}
                  className={classes.tableRow}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(product.id)}
                    />
                  </TableCell>
                  <TableCellAvatar
                    thumbnail={maybe(() => product.thumbnail.url)}
                  />
                  <TableCell className={classes.colName}>
                    {maybe<React.ReactNode>(() => product.name, <Skeleton />)}
                  </TableCell>
                  <TableCell className={classes.colType}>
                    {maybe<React.ReactNode>(
                      () => product.productType.name,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colPublished}>
                    {product && product.isPublished !== undefined ? (
                      <StatusLabel
                        label={
                          product.isPublished
                            ? i18n.t("Published", { context: "product status" })
                            : i18n.t("Not published", {
                                context: "product status"
                              })
                        }
                        status={product.isPublished ? "success" : "error"}
                      />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.iconCell}>
                    <IconButton
                      disabled={!product || disabled}
                      onClick={event => {
                        event.stopPropagation();
                        onProductUnassign(product.id);
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
                <TableCell colSpan={6}>{i18n.t("No products found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
DiscountProducts.displayName = "DiscountProducts";
export default DiscountProducts;
