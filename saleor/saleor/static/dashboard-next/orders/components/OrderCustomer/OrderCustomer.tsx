import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import ExternalLink from "@saleor/components/ExternalLink";
import Form from "@saleor/components/Form";
import Hr from "@saleor/components/Hr";
import Link from "@saleor/components/Link";
import SingleAutocompleteSelectField from "@saleor/components/SingleAutocompleteSelectField";
import Skeleton from "@saleor/components/Skeleton";
import { SearchCustomers_customers_edges_node } from "../../../containers/SearchCustomers/types/SearchCustomers";
import { customerUrl } from "../../../customers/urls";
import i18n from "../../../i18n";
import { createHref, maybe } from "../../../misc";
import { OrderDetails_order } from "../../types/OrderDetails";

const styles = (theme: Theme) =>
  createStyles({
    sectionHeader: {
      alignItems: "center",
      display: "flex",
      marginBottom: theme.spacing.unit * 3
    },
    sectionHeaderTitle: {
      flex: 1,
      fontWeight: 600 as 600,
      lineHeight: 1,
      textTransform: "uppercase"
    },
    sectionHeaderToolbar: {
      marginRight: -theme.spacing.unit * 2
    },
    userEmail: {
      fontWeight: 600 as 600,
      marginBottom: theme.spacing.unit
    }
  });

export interface OrderCustomerProps extends WithStyles<typeof styles> {
  order: OrderDetails_order;
  users?: SearchCustomers_customers_edges_node[];
  loading?: boolean;
  canEditAddresses: boolean;
  canEditCustomer: boolean;
  fetchUsers?: (query: string) => void;
  onCustomerEdit?: (data: { user?: string; userEmail?: string }) => void;
  onProfileView: () => void;
  onBillingAddressEdit?: () => void;
  onShippingAddressEdit?: () => void;
}

const OrderCustomer = withStyles(styles, { name: "OrderCustomer" })(
  ({
    classes,
    canEditAddresses,
    canEditCustomer,
    fetchUsers,
    loading,
    order,
    users,
    onCustomerEdit,
    onBillingAddressEdit,
    onProfileView,
    onShippingAddressEdit
  }: OrderCustomerProps) => {
    const [isInEditMode, setEditModeStatus] = React.useState(false);
    const toggleEditMode = () => setEditModeStatus(!isInEditMode);

    const billingAddress = maybe(() => order.billingAddress);
    const shippingAddress = maybe(() => order.shippingAddress);
    const user = maybe(() => order.user);
    return (
      <Card>
        <CardTitle
          title={i18n.t("Customer")}
          toolbar={
            !!canEditCustomer && (
              <Button
                color="primary"
                variant="text"
                disabled={!onCustomerEdit}
                onClick={toggleEditMode}
              >
                {i18n.t("Edit")}
              </Button>
            )
          }
        />
        <CardContent>
          {user === undefined ? (
            <Skeleton />
          ) : isInEditMode && canEditCustomer ? (
            <Form initial={{ query: { label: "", value: "" } }}>
              {({ change, data }) => {
                const handleChange = (event: React.ChangeEvent<any>) => {
                  change(event);
                  onCustomerEdit({
                    [event.target.value.value.includes("@")
                      ? "userEmail"
                      : "user"]: event.target.value.value
                  });
                  toggleEditMode();
                };
                return (
                  <SingleAutocompleteSelectField
                    custom={true}
                    choices={maybe(() => users, []).map(user => ({
                      label: user.email,
                      value: user.id
                    }))}
                    fetchChoices={fetchUsers}
                    loading={loading}
                    placeholder={i18n.t("Search Customers")}
                    onChange={handleChange}
                    name="query"
                    value={data.query}
                  />
                );
              }}
            </Form>
          ) : user === null ? (
            <Typography>{i18n.t("Anonymous user")}</Typography>
          ) : (
            <>
              <Typography className={classes.userEmail}>
                {user.email}
              </Typography>
              <div>
                <Link
                  underline={false}
                  href={createHref(customerUrl(user.id))}
                  onClick={onProfileView}
                >
                  {i18n.t("View Profile")}
                </Link>
              </div>
              {/* TODO: Uncomment it after adding ability to filter
                    orders by customer */}
              {/* <div>
                    <Link underline={false} href={}>{i18n.t("View Orders")}</Link>
                  </div> */}
            </>
          )}
        </CardContent>
        <Hr />
        <CardContent>
          <div className={classes.sectionHeader}>
            <Typography className={classes.sectionHeaderTitle}>
              {i18n.t("Contact information")}
            </Typography>
          </div>

          {maybe(() => order.userEmail) === undefined ? (
            <Skeleton />
          ) : order.userEmail === null ? (
            <Typography>{i18n.t("Not set")}</Typography>
          ) : (
            <ExternalLink
              href={`mailto:${maybe(() => order.userEmail)}`}
              typographyProps={{ color: "primary" }}
            >
              {maybe(() => order.userEmail)}
            </ExternalLink>
          )}
        </CardContent>
        <Hr />
        <CardContent>
          <div className={classes.sectionHeader}>
            <Typography className={classes.sectionHeaderTitle}>
              {i18n.t("Shipping Address")}
            </Typography>
            {canEditAddresses && (
              <div className={classes.sectionHeaderToolbar}>
                <Button
                  color="primary"
                  variant="text"
                  onClick={onShippingAddressEdit}
                  disabled={!onShippingAddressEdit && user === undefined}
                >
                  {i18n.t("Edit")}
                </Button>
              </div>
            )}
          </div>
          {shippingAddress === undefined ? (
            <Skeleton />
          ) : shippingAddress === null ? (
            <Typography>{i18n.t("Not set")}</Typography>
          ) : (
            <>
              {shippingAddress.companyName && (
                <Typography>{shippingAddress.companyName}</Typography>
              )}
              <Typography>
                {shippingAddress.firstName} {shippingAddress.lastName}
              </Typography>
              <Typography>
                {shippingAddress.streetAddress1}
                <br />
                {shippingAddress.streetAddress2}
              </Typography>
              <Typography>
                {shippingAddress.postalCode} {shippingAddress.city}
                {shippingAddress.cityArea
                  ? ", " + shippingAddress.cityArea
                  : ""}
              </Typography>
              <Typography>
                {shippingAddress.countryArea
                  ? shippingAddress.countryArea +
                    ", " +
                    shippingAddress.country.country
                  : shippingAddress.country.country}
              </Typography>
              <Typography>{shippingAddress.phone}</Typography>
            </>
          )}
        </CardContent>
        <Hr />
        <CardContent>
          <div className={classes.sectionHeader}>
            <Typography className={classes.sectionHeaderTitle}>
              {i18n.t("Billing Address")}
            </Typography>
            {canEditAddresses && (
              <div className={classes.sectionHeaderToolbar}>
                <Button
                  color="primary"
                  variant="text"
                  onClick={onBillingAddressEdit}
                  disabled={!onBillingAddressEdit && user === undefined}
                >
                  {i18n.t("Edit")}
                </Button>
              </div>
            )}
          </div>
          {billingAddress === undefined ? (
            <Skeleton />
          ) : billingAddress === null ? (
            <Typography>{i18n.t("Not set")}</Typography>
          ) : maybe(() => shippingAddress.id) === billingAddress.id ? (
            <Typography>{i18n.t("Same as shipping address")}</Typography>
          ) : (
            <>
              {billingAddress.companyName && (
                <Typography>{billingAddress.companyName}</Typography>
              )}
              <Typography>
                {billingAddress.firstName} {billingAddress.lastName}
              </Typography>
              <Typography>
                {billingAddress.streetAddress1}
                <br />
                {billingAddress.streetAddress2}
              </Typography>
              <Typography>
                {billingAddress.postalCode} {billingAddress.city}
                {billingAddress.cityArea ? ", " + billingAddress.cityArea : ""}
              </Typography>
              <Typography>
                {billingAddress.countryArea
                  ? billingAddress.countryArea +
                    ", " +
                    billingAddress.country.country
                  : billingAddress.country.country}
              </Typography>
              <Typography>{billingAddress.phone}</Typography>
            </>
          )}
        </CardContent>
      </Card>
    );
  }
);
OrderCustomer.displayName = "OrderCustomer";
export default OrderCustomer;
