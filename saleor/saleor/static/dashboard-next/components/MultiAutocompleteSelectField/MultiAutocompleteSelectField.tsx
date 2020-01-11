import CircularProgress from "@material-ui/core/CircularProgress";
import MenuItem from "@material-ui/core/MenuItem";
import Paper from "@material-ui/core/Paper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Downshift, { ControllerStateAndHelpers } from "downshift";
import React from "react";

import i18n from "../../i18n";
import ArrowDropdownIcon from "../../icons/ArrowDropdown";
import Debounce, { DebounceProps } from "../Debounce";

interface ChoiceType {
  label: string;
  value: string;
}

const styles = (theme: Theme) =>
  createStyles({
    chip: {
      margin: `${theme.spacing.unit / 2}px ${theme.spacing.unit / 2}px`
    },
    container: {
      flexGrow: 1,
      position: "relative"
    },
    paper: {
      left: 0,
      marginTop: theme.spacing.unit,
      padding: theme.spacing.unit,
      position: "absolute",
      right: 0,
      zIndex: 2
    }
  });

export interface MultiAutocompleteSelectFieldChildrenFunc {
  deleteItem: (item: ChoiceType) => void;
  items: ChoiceType[];
}
export type MultiAutocompleteSelectFieldChildren = (
  props: MultiAutocompleteSelectFieldChildrenFunc
) => React.ReactNode;

export interface MultiAutocompleteSelectFieldProps
  extends WithStyles<typeof styles> {
  name: string;
  children: MultiAutocompleteSelectFieldChildren;
  choices: ChoiceType[];
  value?: ChoiceType[];
  loading?: boolean;
  placeholder?: string;
  helperText?: string;
  label?: string;
  fetchChoices(value: string);
  onChange(event);
}

const DebounceAutocomplete: React.ComponentType<
  DebounceProps<string>
> = Debounce;

export const MultiAutocompleteSelectField = withStyles(styles, {
  name: "MultiAutocompleteSelectField"
})(
  ({
    children,
    choices,
    classes,
    helperText,
    label,
    loading,
    name,
    placeholder,
    value,
    fetchChoices,
    onChange
  }: MultiAutocompleteSelectFieldProps) => {
    const handleSelect = (
      item: ChoiceType,
      { reset }: ControllerStateAndHelpers
    ) => {
      reset({ inputValue: "" });
      onChange({ target: { name, value: [...value, item] } });
    };
    const handleDelete = (item: ChoiceType) => {
      const newValue = value.slice();
      newValue.splice(
        value.findIndex(listItem => listItem.value === item.value),
        1
      );
      onChange({ target: { name, value: newValue } });
    };

    const filteredChoices = choices.filter(
      suggestion => value.map(v => v.value).indexOf(suggestion.value) === -1
    );

    return (
      <DebounceAutocomplete debounceFn={fetchChoices}>
        {debounce => (
          <Downshift
            selectedItem={value}
            itemToString={item => (item ? item.label : "")}
            onSelect={handleSelect}
            onInputValueChange={value => debounce(value)}
          >
            {({
              getInputProps,
              getItemProps,
              isOpen,
              selectedItem,
              toggleMenu,
              closeMenu,
              openMenu,
              highlightedIndex
            }) => {
              return (
                <div className={classes.container}>
                  <TextField
                    InputProps={{
                      ...getInputProps({
                        placeholder
                      }),
                      endAdornment: (
                        <div>
                          {loading ? (
                            <CircularProgress size={20} />
                          ) : (
                            <ArrowDropdownIcon onClick={toggleMenu} />
                          )}
                        </div>
                      ),
                      id: undefined,
                      onBlur: closeMenu,
                      onFocus: openMenu
                    }}
                    helperText={helperText}
                    label={label}
                    fullWidth={true}
                  />
                  {isOpen && (
                    <Paper className={classes.paper} square>
                      {!loading && filteredChoices.length > 0
                        ? filteredChoices.map((suggestion, index) => (
                            <MenuItem
                              key={suggestion.value}
                              selected={highlightedIndex === index}
                              component="div"
                              {...getItemProps({ item: suggestion })}
                            >
                              {suggestion.label}
                            </MenuItem>
                          ))
                        : !loading && (
                            <MenuItem disabled={true} component="div">
                              {i18n.t("No results found")}
                            </MenuItem>
                          )}
                    </Paper>
                  )}
                  {children({
                    deleteItem: handleDelete,
                    items: selectedItem
                  })}
                </div>
              );
            }}
          </Downshift>
        )}
      </DebounceAutocomplete>
    );
  }
);
MultiAutocompleteSelectField.displayName = "MultiAutocompleteSelectField";
export default MultiAutocompleteSelectField;
