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
    onAddToCartError: PropTypes.func.isRequired,
    onAddToCartSuccess: PropTypes.func.isRequired,
    store: PropTypes.object.isRequired,
    url: PropTypes.string.isRequired
  };

  constructor (props) {
    super(props);
    const params = queryString.parse(location.search);
        
    let t = '';
    if (typeof(params['kinase_type']) == "undefined" || params['kinase_type'] == 'human'){
      t = 'Human Only';
    }
    else{
      t = 'All';
    }
    
    this.state = {
      selection: t
    };
  }

  handleAttributeChange = (value) => {
    let _type = '';
    let selection = this.state.selection;
    if (value == 'Human Only'){
      _type = 'human';
    }
    else{
      _type = 'all';
    }
    
    if (value != selection){
      window.location.href = this.props.url + '?kinase_type=' + _type;
    }
  };
  

  render () {
    const { kinase_type, selection } = this.state;
    let kinase_Types = ['All', 'Human Only']
    let kinase_Tips = ['selectivity over all predictable kinases', 'selectivity over predictable human kinases']

    const addToCartBtnClasses = classNames({
      'btn primary': true,
      'disabled': false
    });

    return (
      <div>
        <AttributeSelectionWidget
          kinomeTypes={kinase_Types}
          kinomeTips={kinase_Tips}
          selection={selection}
          handleAttributeChange={this.handleAttributeChange}
        />
      </div>
    );
  }
});
