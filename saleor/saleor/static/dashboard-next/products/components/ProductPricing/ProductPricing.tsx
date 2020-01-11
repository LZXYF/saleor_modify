import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import ControlledCheckbox from "@saleor/components/ControlledCheckbox";
import PriceField from "@saleor/components/PriceField";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    }
  });

interface ProductPricingProps extends WithStyles<typeof styles> {
  currency?: string;
  data: {
    chargeTaxes: boolean;
    basePrice: number;
  };
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const ProductPricing = withStyles(styles, { name: "ProductPricing" })(
  ({ classes, currency, data, disabled, onChange }: ProductPricingProps) => (
    <Card>
      <CardTitle title={i18n.t("Pricing")}>
        <ControlledCheckbox
          name="chargeTaxes"
          label={i18n.t("Charge taxes for this item")}
          checked={data.chargeTaxes}
          onChange={onChange}
          disabled={disabled}
        />
      </CardTitle>
      <CardContent>
        <div className={classes.root}>
          <PriceField
            disabled={disabled}
            label={i18n.t("Price")}
            name="basePrice"
            value={data.basePrice}
            currencySymbol={currency}
            onChange={onChange}
          />
        </div>
      </CardContent>
    </Card>
  )
);
ProductPricing.displayName = "ProductPricing";
export default ProductPricing;
