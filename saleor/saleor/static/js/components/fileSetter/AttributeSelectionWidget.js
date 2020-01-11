import React, { Component } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

export default class AttributeSelectionWidget extends Component {
  
  static propTypes = {
    errors: PropTypes.array,
    handleAttributeChange: PropTypes.func.isRequired
  };

  handleChange = (value) => {
    this.props.handleAttributeChange(value);
  }

  render() {
    let kinomeTypes = ['download'];
    let value = kinomeTypes[0];
    
    const labelClass = classNames({
      'btn btn-secondary variant-picker__option': true,
      'active': true
    });
    
    return (
        <div className="btn-group" data-toggle="buttons">
          <label
            className={labelClass}
            onClick={() => this.handleChange(value)}>
            <input
              defaultChecked="true"
              name={value}
              type="radio" />
            {value}
          </label>
        </div>
    );
  }
}
