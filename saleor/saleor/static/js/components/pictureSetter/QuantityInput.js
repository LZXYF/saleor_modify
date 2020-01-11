import classNames from 'classnames';
import React, { Component } from 'react';
import PropTypes from 'prop-types';

export default class QuantityInput extends Component {

  static propTypes = {
    errors: PropTypes.array,
    handleChange: PropTypes.func.isRequired,
    cutoff_ratio: PropTypes.number.isRequired
  }

  render() {
    const { errors, cutoff_ratio, handleChange } = this.props;
    const formGroupClasses = classNames({
      'form-group': false,
      'product__info__quantity': true
    });
    return (
      <div className={formGroupClasses}>
        <label className="control-label product__variant-picker__label" htmlFor="id_cutoff">{pgettext('Add to cart form field label', 'Cut-off')}</label>
        <input
          className="form-control"
          max="1"
          min="0"
          defaultValue="0.5"
          id="id_cutoff"
          name="cutoff_ratio"
          onChange={handleChange}
          type="number"
        />
      </div>
    );
  }
}
