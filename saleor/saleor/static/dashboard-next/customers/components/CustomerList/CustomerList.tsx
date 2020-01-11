import Card from "@material-ui/core/Card";
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
import React from "react";

import Checkbox from "@saleor/components/Checkbox";
import Skeleton from "@saleor/components/Skeleton";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "../../../i18n";
import { getUserName, maybe, renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { ListCustomers_customers_edges_node } from "../../types/ListCustomers";

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colEmail: {},
      colName: {},
      colOrders: {
        width: 200
      }
    },
    colEmail: {},
    colName: {},
    colOrders: {
      textAlign: "center"
    },
    tableRow: {
      cursor: "pointer"
    }
  });

export interface CustomerListProps
  extends ListProps,
    ListActions,
    WithStyles<typeof styles> {
  customers: ListCustomers_customers_edges_node[];
}

const CustomerList = withStyles(styles, { name: "CustomerList" })(
  ({
    classes,
    disabled,
    customers,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick,
    toolbar,
    toggle,
    toggleAll,
    selected,
    isChecked
  }: CustomerListProps) => (
    <Card>
      <Table>
        <TableHead
          selected={selected}
          disabled={disabled}
          items={customers}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell className={classes.colName}>
            {i18n.t("Customer Name", { context: "table header" })}
          </TableCell>
          <TableCell className={classes.colEmail}>
            {i18n.t("Customer e-mail", { context: "table header" })}
          </TableCell>
          <TableCell className={classes.colOrders}>
            {i18n.t("Orders", { context: "table header" })}
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
            customers,
            customer => {
              const isSelected = customer ? isChecked(customer.id) : false;

              return (
                <TableRow
                  className={!!customer ? classes.tableRow : undefined}
                  hover={!!customer}
                  key={customer ? customer.id : "skeleton"}
                  selected={isSelected}
                  onClick={customer ? onRowClick(customer.id) : undefined}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(customer.id)}
                    />
                  </TableCell>
                  <TableCell className={classes.colName}>
                    {getUserName(customer)}
                  </TableCell>
                  <TableCell className={classes.colEmail}>
                    {maybe<React.ReactNode>(() => customer.email, <Skeleton />)}
                  </TableCell>
                  <TableCell className={classes.colOrders}>
                    {maybe<React.ReactNode>(
                      () => customer.orders.totalCount,
                      <Skeleton />
                    )}
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={4}>
                  {i18n.t("No customers found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
CustomerList.displayName = "CustomerList";
export default CustomerList;
