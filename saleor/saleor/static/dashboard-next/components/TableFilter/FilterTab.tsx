import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Tab from "@material-ui/core/Tab";
import classNames from "classnames";
import React from "react";

const styles = (theme: Theme) =>
  createStyles({
    selectedTabLabel: {
      "&$tabLabel": {
        color: theme.typography.body2.color
      }
    },
    tabLabel: {
      "&:hover": {
        color: theme.typography.body2.color
      },
      color: theme.typography.caption.color,
      fontSize: "1rem",
      fontWeight: 400
    },
    tabRoot: {
      minWidth: "80px",
      opacity: 1,
      paddingTop: `${theme.spacing.unit * 1}px`,
      textTransform: "initial" as "initial"
    }
  });

interface FilterTabProps extends WithStyles<typeof styles> {
  onClick: () => void;
  label: string;
  selected?: boolean;
  value?: number;
}

export const FilterTab = withStyles(styles, { name: "FilterTab" })(
  ({ classes, onClick, label, selected, value }: FilterTabProps) => (
    <Tab
      disableRipple
      label={label}
      classes={{
        label: classNames(classes.tabLabel, {
          [classes.selectedTabLabel]: selected
        }),
        root: classes.tabRoot
      }}
      onClick={onClick}
      value={value}
    />
  )
);
FilterTab.displayName = "FilterTab";
export default FilterTab;
