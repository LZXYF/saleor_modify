import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import { ControlledCheckbox } from "@saleor/components/ControlledCheckbox";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { FormData } from "../VoucherDetailsPage";

interface VoucherLimitsProps {
  data: FormData;
  defaultCurrency: string;
  disabled: boolean;
  errors: FormErrors<"usageLimit">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const VoucherLimits = ({
  data,
  disabled,
  errors,
  onChange
}: VoucherLimitsProps) => {
  return (
    <Card>
      <CardTitle title={i18n.t("Usage Limit ")} />
      <CardContent>
        <ControlledCheckbox
          checked={data.hasUsageLimit}
          label={i18n.t(
            "Limit number of times this discount can be used in total"
          )}
          name={"hasUsageLimit" as keyof FormData}
          onChange={onChange}
        />
        {data.hasUsageLimit && (
          <TextField
            disabled={disabled}
            error={!!errors.usageLimit}
            helperText={errors.usageLimit}
            label={i18n.t("Limit of Uses")}
            name={"usageLimit" as keyof FormData}
            value={data.usageLimit}
            onChange={onChange}
            type="number"
            inputProps={{
              min: 0
            }}
            fullWidth
          />
        )}
      </CardContent>
    </Card>
  );
};
export default VoucherLimits;
