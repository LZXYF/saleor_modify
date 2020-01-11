import React, { Component } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import Slider from "react-slick";
export default class AttributeSelectionWidget extends Component {

  static propTypes = {
    attribute: PropTypes.object.isRequired,
    handleChange: PropTypes.func.isRequired,
	  //校验文件和显示错误的函数
    handleParameterErrors: PropTypes.func.isRequired,
    handleFileChange: PropTypes.func.isRequired,
    selected: PropTypes.string
  };

  handleChange = (attrPk, valuePk) => {
    this.props.handleChange(attrPk.toString(), valuePk.toString());
  }

//有关文件的函数1——文件类型校验
 handleChangeFileType = (event) =>{
	  try{
		  console.log("进入了这个函数")
		        let f_name = event.target.files[0].name;
		        let index= f_name.lastIndexOf(".");
		        let type = f_name.substr(index);
		        let allowedTypes = event.target.accept.split(", ");
		        let typeAllowed = false;
		        let error_type = 0;
		        allowedTypes.map((item)=>{
				        if(type == item){
						          typeAllowed = true;
						          error_type = 1;
						        }
				      })
		        let file_size = event.target.files[0].size;
		        if(file_size > 2600000){
				        error_type = -2;
				      }
		        if(file_size < 5){
				        error_type = -3;
				      }
		  	console.log("在这里呢");
		        this.props.handleFileChange(event, typeAllowed, error_type);
		  	console.log("执行完成了事件1————————");
		        this.props.handleParameterErrors(error_type);
		      }
	     catch(e){
		           return false;
		         }
	}

  render() {
    const { attribute, selected } = this.props;
    return (
      <div className="variant-picker" >
        <div className="variant-picker__label">{attribute.name}</div>
        <div className="btn-group">
          {attribute.values.map((value, i) => {
            const active = selected === value.pk.toString();
            const labelClass = classNames({
              'btn btn-secondary variant-picker__option': true,
              'active': active
            });
            return (
		<div>
		<div>
		  {value.type_ini=="2"?
		   (
			<input
			id="testfile"
		      	type="file"
			accept=".txt, .sdf, .mol"
		      	onChange={this.handleChangeFileType}
			title="Upload File" 
			className="btn"
	           	/>
		   )
		   :
		   (value.type_ini=="3"?
			(<div>
			  <input type="hidden" id="molecule_flag" value="true" />
			  <p>--Molecule--</p>
			</div>)
		       :
		       (<label
				className={labelClass}
				key={i}
				onClick={() => this.handleChange(attribute.pk, value.pk)}>
				<input
				defaultChecked={active}
				name={value.pk}
				type="radio"/>
		 		{value.name}
		     	</label>)
		   )
		  }
    		</div>
	     </div>    
            );
          })}
        </div>
      </div>
    );
  }
}
