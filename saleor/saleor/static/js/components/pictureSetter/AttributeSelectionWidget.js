import React, { Component } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import ReactTooltip from 'react-tooltip'

export default class AttributeSelectionWidget extends Component {
  
  static propTypes = {
    errors: PropTypes.array,
    variantAttributes: PropTypes.object.isRequired,
    selection: PropTypes.object.isRequired,
    handleAttributeChange: PropTypes.func.isRequired
  };

  handleChange = (value) => {
    this.props.handleAttributeChange(value);
  }

  render() {
    const { errors, kinomeTypes, kinomeTips, selection } = this.props;
    
    return (
      <div>
        <div className="btn-group" data-toggle="buttons">
          {kinomeTypes.map((value, i) => {
            const active = selection === value;
            const labelClass = classNames({
              'btn btn-secondary variant-picker__option': true,
              'active': active
            });
            return (
            <div data-tip={kinomeTips[i]}>
              <label
                className={labelClass}
                key={i}
                onClick={() => this.handleChange(value)}>
                <input
                  defaultChecked={active}
                  name={value}
                  type="radio" />
                {value}
                <ReactTooltip place="bottom" type="info" effect="float"/>
              </label>
            </div>
            );
          }
          )}
        </div>
      </div>
    );
  }
}
