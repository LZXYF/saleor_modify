import _ from 'lodash';
import $ from 'jquery';
import classNames from 'classnames';
import { observer } from 'mobx-react';
import React, { Component } from 'react';
import PropTypes from 'prop-types';

import Slider from "react-slick";

import AttributeSelectionWidget from './AttributeSelectionWidget';
import QuantityInput from './QuantityInput';
import * as queryString from 'query-string';

export default observer(class VariantPicker extends Component {
  static propTypes = {
    onAddToCheckoutError: PropTypes.func.isRequired,
    onAddToCheckoutSuccess: PropTypes.func.isRequired,
    store: PropTypes.object.isRequired,
    url: PropTypes.string.isRequired,
    variantAttributes: PropTypes.array.isRequired,
    variants: PropTypes.array.isRequired
  };

  constructor (props) {

    super(props);
    const { variants } = this.props;
    const variant = variants.filter(v => !!Object.keys(v.attributes).length)[0];
    const { dkftest } = variant;
    const params = queryString.parse(location.search);
    let selection = {};
    if (Object.keys(params).length) {
      Object.keys(params)
        .some((name) => {
          const valueName = params[name];
          const attribute = this.matchAttributeBySlug(name);
          const value = this.matchAttributeValueByName(attribute, valueName);
          if (attribute && value) {
            selection[attribute.pk] = value.pk.toString();
          } else {
            selection = variant ? variant.attributes : {};
            return true;
          }
        });
    } else if (Object.keys(variant).length) {
      selection = variant.attributes;
    }
    //修改State
    this.state = {
      errors: {},
      quantity: 1,
      selection: selection,
      typeSelection: "Upload File",
      upload_file: null,
      file_name: "",  
      style: "",
      activeSlidie:-1
    };
    this.matchVariantFromSelection();
  }

  checkVariantAvailability = () => {
    const { store } = this.props;
    return store.variant.availability;
  };

  handelTestdkftest = () => {
    alert("这是一个测试数据的按钮");
  }

	//有关文件的函数5——修改该函数，使能上传文件
  handleAddToCheckout = () => {
    const { onAddToCheckoutSuccess, onAddToCheckoutError, store } = this.props;
    const { quantity, file_name, upload_file } = this.state;
    if (quantity > 0 && !store.isEmpty) {
	    //包装form表单，提交此表单
	     var formData = new FormData();
	            formData.append('quantity', quantity);
	            formData.append('variant', store.variant.id);
	            formData.append('upload_file', upload_file);
	            formData.append('file_name', file_name);
	    console.log("文件名是——",file_name);
      $.ajax({
        url: this.props.url,   //根据这个url可以找到请求处理函数：saleor/product/views.product_add_to_cart()
        method: 'post',
	contentType: false,
	processData: false,
        data: formData,
        success: () => {
          onAddToCheckoutSuccess();
        },
        error: (response) => {
          onAddToCheckoutError(response);
        }
      });
    }
  };

  handleAttributeChange = (attrId, valueId) => {
     this.resetParameters();

    this.setState({
      selection: Object.assign({}, this.state.selection, { [attrId]: valueId })
    }, () => {
      this.matchVariantFromSelection();
      let params = {};
      Object.keys(this.state.selection)
        .forEach(attrId => {
          const attribute = this.matchAttribute(attrId);
          const value = this.matchAttributeValue(attribute, this.state.selection[attrId]);
          if (attribute && value) {
            params[attribute.slug] = value.slug;
          }
        });
      history.pushState(null, null, '?' + queryString.stringify(params));
    });
  };

  handleQuantityChange = (event) => {
	   this.resetParameters();

    this.setState({ quantity: parseInt(event.target.value) });
  };
	//有关文件函数4——清除文件错误信息和State,在每个change函数里面调用一次
	resetParameters(){
		    let warning = document.getElementById("warning");
		    warning.innerHTML = "";
		    this.setState({ upload_file: null, file_name: "" });
		  }

	//有关文件的函数3——保存上传文件到State
	handleFileChange = (event, type_allowed, error_type) => {
		    console.log("刚来到函数2");
			this.resetParameters();
		    console.log("这里执行了函数2————————") 
		    if (type_allowed && error_type == 1){
			          const file = event.target.files[0];
			          const name = event.target.files[0].name;
			          let ind = name.lastIndexOf(".");
			          let tpe = name.substr(ind + 1)
			          let revised_n = name.substr(0, ind).replace(/[^\w_]/g,'_') + '.' + tpe
			          this.setState({ upload_file: file, file_name: revised_n })
			        }
		  };

	//有关文件的函数2————显示上传错误信息
	handleParameterErrors = (error_type) => {
		    let warning = document.getElementById("warning");
		    if (error_type == 0){
			          warning.innerHTML = "File Type Not Supported.";
			          return false;
			        }
		    if (error_type == -1){
			          warning.innerHTML = "Please Submit A Molecule";
			          return false;
			        }
		    if (error_type == -2){
			          warning.innerHTML = "File Size Limit Exceeded.";
			          return false;
			        }
		    if (error_type == -3){
			          warning.innerHTML = "Empty Parameter File Not Allowed.";
			          return false;
			        }
		    return true;
	};


   //只有第一次渲染时，不调用，其它冲渲染之前都会调用的React钩子函数
  shouldComponentUpdate = (nextProps, nextState) => {
	console.log(nextState.activeSlide)
	//获取当前页码的div（马上出现的页）
	var $current = $(".slick-track").find(".slick-slide[data-index='"+ nextState.activeSlide +"']");
	console.log($current.text());
	 //判断自定义的标识符
	if($current.find("#molecule_flag").val() == "true"){
		//隐藏商品图片
	      $(".carousel-item>.product-image").css({"display":"none"});
	       //显示分子式模板
	       $(".carousel-item>#sketch-test").css({"display":"block"});
	      //$(".carousel-item").append("<div id='sketch' data-toolbars='reporting'></div>");
	}else{
		//显示商品图片
	      $(".carousel-item>.product-image").css({"display":"block"});
		//删除分子式模板
	      //$(".carousel-item>#sketch").remove();
	      $(".carousel-item>#sketch-test").css({"display":"none"});
	}
	return true;
  }


  matchAttribute = (id) => {
    const { variantAttributes } = this.props;
    const match = variantAttributes.filter(attribute => attribute.pk.toString() === id);
    return match.length > 0 ? match[0] : null;
  };

  matchAttributeBySlug = (slug) => {
    const { variantAttributes } = this.props;
    const match = variantAttributes.filter(attribute => attribute.slug === slug);
    return match.length > 0 ? match[0] : null;
  };

  matchAttributeValue = (attribute, id) => {
    const match = attribute.values.filter(attribute => attribute.pk.toString() === id);
    return match.length > 0 ? match[0] : null;
  };

  matchAttributeValueByName = (attribute, name) => {
    const match = attribute ? attribute.values.filter(value => value.slug === name) : [];
    return match.length > 0 ? match[0] : null;
  };

  matchVariantFromSelection () {
    const { store, variants } = this.props;
    let matchedVariant = null;
    variants.forEach(variant => {
      if (_.isEqual(this.state.selection, variant.attributes)) {
        matchedVariant = variant;
      }
    });
    store.setVariant(matchedVariant);
  }



  componentDidMount(){
	$(".slick-dots").prepend($(".slick-prev").css({"position":"relative","display":"inline-block","top":"0px"}));
	$(".slick-dots").append($(".slick-next").css({"position":"relative","display":"inline-block","top":"0px"}));
	  $(".carousel-item").append("<div class='resizable' id='sketch-test'><iframe src='/static/marvinjs/editorws.html' id='sketch' class='sketcher-frame'></iframe></div>");
	  $(".carousel-item>#sketch-test").css({"display":"none"});
	//$(".slick-slider>.slick-arrow").remove();	
 }

  render () {
	  const settings = {
		        dots: true,
		        infinite: true,
		        speed: 500,
		        slidesToShow: 1,
		        slidesToScroll: 1,
		  	beforeChange: (current,next) => this.setState({ activeSlide: next })
		  //afterChange: current => this.setState({ activeSlide: current })
		      };
    const { store, variantAttributes } = this.props;
    const { errors, selection, quantity, upload_file, file_name } = this.state;
    const disableAddToCheckout = store.isEmpty || !this.checkVariantAvailability();

    const addToCheckoutBtnClasses = classNames({
      'btn btn-primary': true,
      'disabled': disableAddToCheckout
    });
     return (
          <div>
		<Slider ref={c => (this.slider == c)} {...settings}>
            {
                variantAttributes.map((attribute, i) =>
                  <AttributeSelectionWidget
		   ref="child" 
	           onRef={this.onRef}
                   attribute={attribute}
                   handleChange={this.handleAttributeChange}
                   key={i}
                   selected={selection[attribute.pk]}
		   upload_file={upload_file}
	 	   handleParameterErrors={this.handleParameterErrors}
		   handleFileChange={this.handleFileChange}
                 />
               )
            }
	     </Slider>
	     <div className="variant-picker__warning"><span id="warning"></span></div>
	      <div className="clearfix">
              <div className="form-group product__info__button">
                <button
                  className={addToCheckoutBtnClasses}
                  onClick={this.handleAddToCheckout}
                  disabled={disableAddToCheckout}>
                  {pgettext('Product details primary action', 'Add to cart')}
                </button>
              </div>
	     </div>
         </div>
      );

    }
    
});
