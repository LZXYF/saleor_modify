import _ from 'lodash';
import $ from 'jquery';
import classNames from 'classnames';
import { observer } from 'mobx-react';
import React, { Component } from 'react';
import PropTypes from 'prop-types';

import AttributeSelectionWidget from './AttributeSelectionWidget';
import * as queryString from 'query-string';

export default observer(class VariantPicker extends Component {
  static propTypes = {
    url: PropTypes.string.isRequired
  };

  constructor (props) {
    super(props);
  }

  handleAttributeChange = (value) => {
    window.location.href = this.props.url;
  };
  

  render () {
    return (
      <div>
        <AttributeSelectionWidget
          handleAttributeChange={this.handleAttributeChange}
        />
      </div>
    );
  }
});
