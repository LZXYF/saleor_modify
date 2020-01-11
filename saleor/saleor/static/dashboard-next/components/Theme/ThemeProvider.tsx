// FIXME: https://github.com/mirumee/saleor/issues/4174
import OldMuiThemeProvider from "@material-ui/core/styles/MuiThemeProvider";
import MuiThemeProvider from "@material-ui/styles/ThemeProvider";
import React from "react";

import Baseline from "../../Baseline";
import createTheme, { IThemeColors } from "../../theme";

const dark: IThemeColors = {
  autofill: "#5D5881",
  background: {
    default: "#1D1E1F",
    paper: "#2E2F31"
  },
  error: "#C22D74",
  font: {
    default: "#FCFCFC",
    gray: "#9E9D9D"
  },
  gray: {
    default: "#202124",
    disabled: "rgba(32, 33, 36, 0.6)"
  },
  input: {
    default: "#25262A",
    disabled: "#292A2D",
    focused: "#25262A"
  },
  paperBorder: "#252728",
  primary: "#13BEBB",
  secondary: "#21125E"
};
const light: IThemeColors = {
  autofill: "#f4f6c5",
  background: {
    default: "#F1F6F6",
    paper: "#FFFFFF"
  },
  error: "#C22D74",
  font: {
    default: "#3D3D3D",
    gray: "#616161"
  },
  gray: {
    default: "#C8C8C8",
    disabled: "rgba(216, 216, 216, 0.3)"
  },
  input: {
    default: "#F1F6F6",
    disabled: "#EAEAEA",
    focused: "#DCEBEB"
  },
  paperBorder: "#EAEAEA",
  primary: "#13BEBB",
  secondary: "#21125E"
};

interface IThemeContext {
  isDark: boolean;
  toggleTheme: () => void;
}
export const ThemeContext = React.createContext<IThemeContext>({
  isDark: false,
  toggleTheme: () => undefined
});

interface ThemeProviderProps {
  isDefaultDark?: boolean;
}
const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  isDefaultDark
}) => {
  const [isDark, setDark] = React.useState(isDefaultDark);
  const toggleTheme = () => {
    setDark(!isDark);
    localStorage.setItem("theme", (!isDark).toString());
  };

  return (
    <ThemeContext.Provider
      value={{
        isDark,
        toggleTheme
      }}
    >
      <OldMuiThemeProvider theme={createTheme(isDark ? dark : light)}>
        <MuiThemeProvider theme={createTheme(isDark ? dark : light)}>
          <Baseline />
          {children}
        </MuiThemeProvider>
      </OldMuiThemeProvider>
    </ThemeContext.Provider>
  );
};
ThemeProvider.defaultProps = {
  isDefaultDark: false
};
export default ThemeProvider;
